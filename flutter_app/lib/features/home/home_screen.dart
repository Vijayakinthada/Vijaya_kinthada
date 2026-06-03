import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/constants.dart';
import '../../core/scope_storage.dart';
import '../../core/steps/step_milestone.dart';
import '../auth/register_screen.dart';
import '../goals/goals_screen.dart';
import '../history/history_screen.dart';
import '../points/points_screen.dart';
import '../pedometer/pedometer_service.dart';
import '../reminders/reminders_screen.dart';
import '../sessions/log_session_screen.dart';
import '../steps/data/steps_repository_impl.dart';
import '../vitals/vitals_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {
  Map<String, dynamic>? _me;
  bool _loading = true;
  final _pedometer = PedometerService();
  int _liveSteps = 0;
  int _lastSyncedTotal = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _load();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _pedometer.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && _pedometer.isSupported) {
      _startPedometer();
    } else if (state == AppLifecycleState.paused) {
      _pedometer.stop();
    }
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final client = await ApiClient.create();
      final me = await client.me();
      final todaySteps = (me['today_steps'] as num?)?.toInt() ?? 0;
      setState(() {
        _me = me;
        _lastSyncedTotal = todaySteps;
      });
      if (_pedometer.isSupported) _startPedometer();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not load profile: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _startPedometer() async {
    if (_pedometer.isRunning) return;
    final today = DateFormat('yyyy-MM-dd').format(DateTime.now());
    final base = (_me?['today_steps'] as num?)?.toInt() ?? 0;

    await _pedometer.start(onSync: (sessionSteps) async {
      if (!mounted) return;
      setState(() => _liveSteps = sessionSteps);
      final totalToday = base + sessionSteps;

      // Reference: home_cubit onFeedbackState — immediate Snackbar on 100-step milestone
      if (crossedHundredStepMilestone(_lastSyncedTotal, totalToday)) {
        final pts = milestonePointsBetween(_lastSyncedTotal, totalToday);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('+$pts wellness points (every 100 steps)'),
            duration: const Duration(seconds: 2),
          ),
        );
      }

      final client = await ApiClient.create();
      final repo = StepsRepositoryImpl(client);
      final result = await repo.syncDailySteps(
        date: today,
        stepCount: totalToday,
      );
      _lastSyncedTotal = totalToday;

      final awarded = result['points_awarded'] as List<dynamic>? ?? [];
      if (awarded.isNotEmpty && mounted) {
        await _load();
      }
    });
  }

  Future<void> _signOut() async {
    await ScopeStorage.clear();
    _pedometer.stop();
    if (mounted) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(
          builder: (_) => RegisterScreen(
            onRegistered: () => Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const HomeScreen()),
            ),
          ),
        ),
        (_) => false,
      );
    }
  }

  int get _todaySteps {
    final base = (_me?['today_steps'] as num?)?.toInt() ?? 0;
    return base + (_pedometer.isRunning ? _liveSteps : 0);
  }

  int get _stepGoal {
    final goal = _me?['goal'] as Map<String, dynamic>?;
    return (goal?['daily_step_target'] as num?)?.toInt() ?? 5000;
  }

  @override
  Widget build(BuildContext context) {
    final progress = (_todaySteps / _stepGoal).clamp(0.0, 1.0);

    return Scaffold(
      appBar: AppBar(
        title: Text(_me?['display_name'] ?? 'Gentle Activity'),
        actions: [
          IconButton(onPressed: _signOut, icon: const Icon(Icons.logout)),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            wellnessDisclaimer,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              SizedBox(
                                width: 72,
                                height: 72,
                                child: Stack(
                                  alignment: Alignment.center,
                                  children: [
                                    CircularProgressIndicator(
                                      value: progress,
                                      strokeWidth: 6,
                                    ),
                                    Text(
                                      '${(progress * 100).round()}%',
                                      style: Theme.of(context).textTheme.labelSmall,
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '$_todaySteps / $_stepGoal steps',
                                      style: Theme.of(context).textTheme.titleMedium,
                                    ),
                                    Text('Balance: ${_me?['balance'] ?? 0} wellness pts'),
                                    Text(
                                      'Active minutes: ${_me?['today_active_minutes'] ?? 0}',
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  _NavTile(
                    icon: Icons.directions_walk,
                    title: 'Log gentle walk',
                    onTap: () => _open(LogSessionScreen(onSaved: _load)),
                  ),
                  _NavTile(
                    icon: Icons.flag_outlined,
                    title: 'Daily goals',
                    onTap: () => _open(GoalsScreen(onSaved: _load)),
                  ),
                  _NavTile(
                    icon: Icons.notifications_outlined,
                    title: 'Reminders',
                    onTap: () => _open(RemindersScreen(onSaved: _load)),
                  ),
                  _NavTile(
                    icon: Icons.favorite_outline,
                    title: 'BP & pulse',
                    onTap: () => _open(VitalsScreen(onSaved: _load)),
                  ),
                  _NavTile(
                    icon: Icons.swap_horiz,
                    title: 'Exchanges & history',
                    onTap: () => _open(const HistoryScreen()),
                  ),
                  _NavTile(
                    icon: Icons.stars_outlined,
                    title: 'Points & ledger',
                    onTap: () => _open(const PointsScreen()),
                  ),
                  if (_pedometer.isSupported)
                    Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child: Text(
                        _pedometer.isRunning
                            ? 'Foreground step tracking active'
                            : 'Open app to track steps in foreground',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                ],
              ),
            ),
    );
  }

  void _open(Widget screen) {
    Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => screen))
        .then((_) => _load());
  }
}

class _NavTile extends StatelessWidget {
  const _NavTile({
    required this.icon,
    required this.title,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(icon),
        title: Text(title),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
