import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import 'package:http/http.dart' as http;

// 전역 알림 플러그인
final FlutterLocalNotificationsPlugin notificationsPlugin =
    FlutterLocalNotificationsPlugin();

// 전역 상태
String? currentRequestId;
String? currentServerAddress;
WebSocketChannel? globalChannel;
Function()? onRequestHandled;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initNotifications();
  runApp(const ClaudeRemoteApp());
}

Future<void> initNotifications() async {
  const androidSettings =
      AndroidInitializationSettings('@mipmap/ic_launcher');
  const iosSettings = DarwinInitializationSettings();
  const settings =
      InitializationSettings(android: androidSettings, iOS: iosSettings);

  await notificationsPlugin.initialize(
    settings,
    onDidReceiveNotificationResponse: onNotificationAction,
    onDidReceiveBackgroundNotificationResponse: onBackgroundNotificationAction,
  );

  const androidChannel = AndroidNotificationChannel(
    'claude_remote_channel',
    'Claude Remote',
    description: 'Claude Code remote control notifications',
    importance: Importance.high,
  );

  await notificationsPlugin
      .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>()
      ?.createNotificationChannel(androidChannel);
}

void onNotificationAction(NotificationResponse response) async {
  final action = response.actionId;
  if (action == null || action.isEmpty) return;

  String decision = 'deny';
  if (action == 'allow') decision = 'allow';
  else if (action == 'allow_always') decision = 'always';

  final prefs = await SharedPreferences.getInstance();
  await prefs.reload();
  final serverAddress = prefs.getString('server_address');
  final requestId = prefs.getString('current_request_id');

  if (requestId == null || serverAddress == null) return;

  try {
    final host = serverAddress.split(':')[0];
    final url = Uri.parse('http://$host:8765/response');
    await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'request_id': requestId, 'decision': decision}),
    );
    await prefs.remove('current_request_id');
    currentRequestId = null;
    notificationsPlugin.cancel(0);
    onRequestHandled?.call();
  } catch (e) {
    if (globalChannel != null && currentRequestId != null) {
      globalChannel!.sink.add(jsonEncode({
        'type': 'permission_response',
        'request_id': currentRequestId,
        'decision': decision,
      }));
      currentRequestId = null;
      notificationsPlugin.cancel(0);
      onRequestHandled?.call();
    }
  }
}

@pragma('vm:entry-point')
void onBackgroundNotificationAction(NotificationResponse response) async {
  WidgetsFlutterBinding.ensureInitialized();
  final action = response.actionId;
  if (action == null || action.isEmpty) return;

  final prefs = await SharedPreferences.getInstance();
  await prefs.reload();
  final serverAddress = prefs.getString('server_address');
  final requestId = prefs.getString('current_request_id');

  if (serverAddress == null || requestId == null) return;

  String decision = 'deny';
  if (action == 'allow') decision = 'allow';
  else if (action == 'allow_always') decision = 'always';

  try {
    final host = serverAddress.split(':')[0];
    final url = Uri.parse('http://$host:8765/response');
    await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'request_id': requestId, 'decision': decision}),
    );
    await prefs.remove('current_request_id');
  } catch (e) {}
}

Future<void> showPermissionNotification(String title, String body) async {
  final androidDetails = AndroidNotificationDetails(
    'claude_remote_channel',
    'Claude Remote',
    channelDescription: 'Claude Code remote control notifications',
    importance: Importance.max,
    priority: Priority.max,
    category: AndroidNotificationCategory.alarm,
    fullScreenIntent: true,
    styleInformation: BigTextStyleInformation(body, contentTitle: title),
    actions: const <AndroidNotificationAction>[
      AndroidNotificationAction('allow_always', 'Always',
          showsUserInterface: false, cancelNotification: true),
      AndroidNotificationAction('deny', 'Deny',
          showsUserInterface: false, cancelNotification: true),
      AndroidNotificationAction('allow', 'Allow',
          showsUserInterface: false, cancelNotification: true),
    ],
  );
  const iosDetails =
      DarwinNotificationDetails(presentAlert: true, presentSound: true);
  final details =
      NotificationDetails(android: androidDetails, iOS: iosDetails);
  await notificationsPlugin.show(0, title, body, details);
}

class ClaudeRemoteApp extends StatelessWidget {
  const ClaudeRemoteApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Claude Remote',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      darkTheme: ThemeData.dark(useMaterial3: true),
      themeMode: ThemeMode.system,
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {
  final TextEditingController _addressController = TextEditingController();
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  bool _isConnecting = false;
  bool _isConnected = false;
  bool _keepAwake = false;
  WebSocketChannel? _channel;

  int? _currentHwnd;
  String _windowTitle = "";
  Map<String, dynamic>? _currentRequest;
  final List<Map<String, dynamic>> _history = [];

  Timer? _reconnectTimer;
  Timer? _pingTimer;

  // 상태 메시지
  String? _statusMessage;
  bool _statusSuccess = true;
  Timer? _statusTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _loadSettings();
    _requestNotificationPermission();
    onRequestHandled = _onNotificationHandled;
  }

  void _onNotificationHandled() {
    if (_currentRequest != null) {
      setState(() {
        _history.insert(0, {..._currentRequest!, 'type': 'permission', 'decision': 'handled'});
        _currentRequest = null;
      });
    }
  }

  Future<void> _requestNotificationPermission() async {
    final android = notificationsPlugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (android != null) {
      await android.requestNotificationsPermission();
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused) {
      _startPing();
    } else if (state == AppLifecycleState.resumed) {
      _stopPing();
      if (_isConnecting && !_isConnected) _connect();
    }
  }

  void _startPing() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(const Duration(seconds: 25), (_) {
      if (_channel != null && _isConnected) {
        try {
          _channel!.sink.add(jsonEncode({'type': 'ping'}));
        } catch (_) {
          _handleDisconnect();
        }
      }
    });
  }

  void _stopPing() {
    _pingTimer?.cancel();
    _pingTimer = null;
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    _addressController.text =
        prefs.getString('server_address') ?? '192.168.0.10:8766';
    setState(() {});
  }

  Future<void> _saveSettings() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_address', _addressController.text);
    currentServerAddress = _addressController.text;
  }

  void _connect() {
    if (_isConnected) return;

    setState(() => _isConnecting = true);
    _saveSettings();

    try {
      final address = _addressController.text.trim();
      _channel = WebSocketChannel.connect(Uri.parse('ws://$address'));
      globalChannel = _channel;

      _channel!.stream.listen(
        (message) async {
          final data = jsonDecode(message);
          final type = data['type'];

          if (type == 'permission_request') {
            currentRequestId = data['request_id'];
            final prefs = await SharedPreferences.getInstance();
            await prefs.setString('current_request_id', data['request_id']);

            final toolInput = data['tool_input'];
            String body = data['tool_name'] ?? 'Unknown';
            if (toolInput is Map && toolInput['command'] != null) {
              body = toolInput['command'].toString();
            } else if (toolInput is Map && toolInput['file_path'] != null) {
              body = toolInput['file_path'].toString();
            }
            showPermissionNotification('Claude Permission', body);
            setState(() => _currentRequest = Map<String, dynamic>.from(data));

          } else if (type == 'tool_result') {
            setState(() {
              _history.insert(0, {...data, 'type': 'tool_result'});
              if (_history.length > 100) _history.removeLast();
            });

          } else if (type == 'hwnd_update') {
            setState(() {
              _currentHwnd = data['hwnd'];
              _windowTitle = data['title'] ?? '';
            });

          } else if (type == 'history_sync') {
            final list = data['history'] as List;
            setState(() {
              for (var item in list.reversed) {
                _history.add({...item, 'type': 'tool_result'});
              }
            });

          } else if (type == 'window_select') {
            // 여러 Claude 창 중 선택
            final windows = (data['windows'] as List)
                .map((w) => {'hwnd': w['hwnd'], 'title': w['title']})
                .toList();
            _showWindowSelectDialog(windows);

          } else if (type == 'command_result') {
            final success = data['success'] ?? false;
            final error = data['error'];
            _showStatusMessage(
              success ? 'Command sent!' : (error ?? 'Failed to send'),
              success
            );

          } else if (type == 'cmd_result') {
            final success = data['success'] ?? false;
            _showStatusMessage(success ? 'CMD opened!' : 'Failed to open CMD', success);

          } else if (type == 'pong') {
            // keep-alive response
          }
        },
        onError: (_) => _handleDisconnect(),
        onDone: () => _handleDisconnect(),
      );

      setState(() {
        _isConnected = true;
      });
    } catch (e) {
      _handleDisconnect();
    }
  }

  void _handleDisconnect() {
    setState(() => _isConnected = false);
    _channel = null;
    globalChannel = null;

    if (_isConnecting) {
      _reconnectTimer?.cancel();
      _reconnectTimer = Timer(const Duration(seconds: 5), () {
        if (_isConnecting && !_isConnected) _connect();
      });
    }
  }

  void _disconnect() {
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _channel?.sink.close();
    _channel = null;
    globalChannel = null;
    setState(() {
      _isConnecting = false;
      _isConnected = false;
      _currentRequest = null;
      _currentHwnd = null;
      _windowTitle = "";
    });
  }

  void _toggleKeepAwake() async {
    setState(() => _keepAwake = !_keepAwake);
    if (_keepAwake) {
      await WakelockPlus.enable();
    } else {
      await WakelockPlus.disable();
    }
  }

  void _sendCommand() {
    final message = _messageController.text.trim();
    if (message.isEmpty || _channel == null || _currentHwnd == null) return;

    _channel!.sink.add(jsonEncode({
      'type': 'command',
      'hwnd': _currentHwnd,
      'message': message,
    }));

    _messageController.clear();
  }

  void _respondPermission(String decision) async {
    if (_currentRequest == null || _channel == null) return;

    _channel!.sink.add(jsonEncode({
      'type': 'permission_response',
      'request_id': _currentRequest!['request_id'],
      'decision': decision,
    }));

    notificationsPlugin.cancel(0);
    currentRequestId = null;

    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('current_request_id');

    setState(() {
      _history.insert(0, {..._currentRequest!, 'type': 'permission', 'decision': decision});
      _currentRequest = null;
    });
  }

  void _showWindowSelectDialog(List<Map<String, dynamic>> windows) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('Select Claude Window'),
        content: SizedBox(
          width: double.maxFinite,
          child: ListView.builder(
            shrinkWrap: true,
            itemCount: windows.length,
            itemBuilder: (context, index) {
              final w = windows[index];
              return ListTile(
                leading: const Icon(Icons.terminal),
                title: Text(w['title'] ?? 'Unknown'),
                subtitle: Text('HWND: ${w['hwnd']}'),
                onTap: () {
                  Navigator.pop(context);
                  _selectWindow(w['hwnd']);
                },
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );
  }

  void _selectWindow(int hwnd) {
    if (_channel == null) return;
    _channel!.sink.add(jsonEncode({
      'type': 'select_window',
      'hwnd': hwnd,
    }));
  }

  void _refreshWindows() {
    if (_channel == null) return;
    _channel!.sink.add(jsonEncode({'type': 'refresh_windows'}));
  }

  void _openCmd() {
    if (_channel == null) return;
    _channel!.sink.add(jsonEncode({'type': 'open_cmd'}));
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _statusTimer?.cancel();
    _channel?.sink.close();
    _addressController.dispose();
    _messageController.dispose();
    _scrollController.dispose();
    WakelockPlus.disable();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Claude Remote'),
        actions: [
          IconButton(
            icon: Icon(_keepAwake ? Icons.light_mode : Icons.light_mode_outlined),
            onPressed: _toggleKeepAwake,
            tooltip: _keepAwake ? 'Screen on' : 'Screen auto',
          ),
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Icon(
              _isConnected ? Icons.cloud_done : (_isConnecting ? Icons.cloud_queue : Icons.cloud_off),
              color: _isConnected ? Colors.green : (_isConnecting ? Colors.orange : Colors.grey),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // 연결 설정
          Card(
            margin: const EdgeInsets.all(12),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _addressController,
                          decoration: const InputDecoration(
                            labelText: 'Server (IP:Port)',
                            border: OutlineInputBorder(),
                            isDense: true,
                          ),
                          enabled: !_isConnecting,
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        onPressed: _isConnecting ? _disconnect : _connect,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _isConnecting ? Colors.red : Colors.green,
                          foregroundColor: Colors.white,
                        ),
                        child: Text(_isConnecting ? 'Stop' : 'Connect'),
                      ),
                    ],
                  ),
                  if (_isConnected) ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            _currentHwnd != null
                                ? 'HWND: $_currentHwnd ${_windowTitle.isNotEmpty ? "($_windowTitle)" : ""}'
                                : 'No Claude window detected',
                            style: TextStyle(
                              fontSize: 12,
                              color: _currentHwnd != null ? Colors.grey[600] : Colors.orange,
                            ),
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.add_box_outlined, size: 20),
                          onPressed: _openCmd,
                          tooltip: 'Open CMD',
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                        const SizedBox(width: 8),
                        IconButton(
                          icon: const Icon(Icons.refresh, size: 20),
                          onPressed: _refreshWindows,
                          tooltip: 'Refresh windows',
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      ],
                    ),
                    // 상태 메시지 표시
                    AnimatedSize(
                      duration: const Duration(milliseconds: 200),
                      alignment: Alignment.topCenter,
                      child: _statusMessage != null
                          ? Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: AnimatedOpacity(
                                opacity: _statusMessage != null ? 1.0 : 0.0,
                                duration: const Duration(milliseconds: 200),
                                child: Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
                                  decoration: BoxDecoration(
                                    color: _statusSuccess ? Colors.green : Colors.red,
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    _statusMessage!,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ),
                              ),
                            )
                          : const SizedBox.shrink(),
                    ),
                  ],
                ],
              ),
            ),
          ),

          // 권한 요청 카드
          if (_currentRequest != null)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF3E0),
                border: Border.all(color: Colors.orange, width: 2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.warning_amber_rounded, color: Colors.deepOrange, size: 28),
                        const SizedBox(width: 8),
                        const Text('Permission Request',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black87)),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text('Tool: ${_currentRequest!['tool_name']}',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.black87)),
                    Container(
                      margin: const EdgeInsets.only(top: 6),
                      padding: const EdgeInsets.all(10),
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Text(
                        _formatInput(_currentRequest!['tool_input']),
                        style: const TextStyle(fontFamily: 'monospace', fontSize: 13, color: Colors.black87),
                        maxLines: 4,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => _respondPermission('always'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.blueGrey[700],
                              side: BorderSide(color: Colors.blueGrey.shade300),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                            child: const Text('Always'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => _respondPermission('deny'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.red[400],
                              side: BorderSide(color: Colors.red.shade200),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                            child: const Text('Deny'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () => _respondPermission('allow'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.teal[400],
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                            child: const Text('Allow'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

          // 히스토리 리스트
          Expanded(
            child: _history.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.history, size: 48, color: Colors.grey[400]),
                        const SizedBox(height: 8),
                        Text('No activity yet', style: TextStyle(color: Colors.grey[600])),
                      ],
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    itemCount: _history.length,
                    itemBuilder: (_, i) {
                      final item = _history[i];
                      final isPermission = item['type'] == 'permission';
                      final toolName = item['tool_name'] ?? '';
                      final decision = item['decision'];

                      return Card(
                        child: ListTile(
                          leading: Icon(
                            isPermission
                                ? (decision == 'allow' || decision == 'always'
                                    ? Icons.check_circle
                                    : Icons.cancel)
                                : Icons.build,
                            color: isPermission
                                ? (decision == 'allow' || decision == 'always'
                                    ? Colors.green
                                    : Colors.red)
                                : Colors.blue,
                          ),
                          title: Text(toolName),
                          subtitle: Text(
                            _formatInput(item['tool_input']),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          trailing: item['timestamp'] != null
                              ? Text(
                                  item['timestamp'].toString().split(' ').last.substring(0, 5),
                                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                                )
                              : null,
                        ),
                      );
                    },
                  ),
          ),

          // 명령 입력
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 4,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: InputDecoration(
                      hintText: _currentHwnd != null ? 'Send command to Claude...' : 'Connect first...',
                      border: const OutlineInputBorder(),
                      isDense: true,
                    ),
                    enabled: _isConnected && _currentHwnd != null,
                    onSubmitted: (_) => _sendCommand(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: (_isConnected && _currentHwnd != null) ? _sendCommand : null,
                  icon: const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _formatInput(dynamic input) {
    if (input == null) return '';
    if (input is Map && input['command'] != null) return input['command'].toString();
    if (input is Map && input['file_path'] != null) return input['file_path'].toString();
    return input.toString();
  }

  void _showStatusMessage(String message, bool success) {
    _statusTimer?.cancel();
    setState(() {
      _statusMessage = message;
      _statusSuccess = success;
    });
    _statusTimer = Timer(const Duration(seconds: 2), () {
      setState(() => _statusMessage = null);
    });
  }
}
