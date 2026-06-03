import 'dart:async';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:pedometer/pedometer.dart';

typedef StepSyncCallback = Future<void> Function(int sessionSteps);

/// Foreground pedometer — reference: HomeCubit.initPlatformState / onStepCount.
class PedometerService {
  StreamSubscription<StepCount>? _sub;
  int _baseline = 0;
  int _sessionSteps = 0;
  bool _running = false;

  bool get isSupported =>
      !kIsWeb && (Platform.isAndroid || Platform.isIOS);

  bool get isRunning => _running;

  int get sessionSteps => _sessionSteps;

  Future<void> start({required StepSyncCallback onSync}) async {
    if (!isSupported || _running) return;
    _running = true;
    _sessionSteps = 0;
    _baseline = 0;

    _sub = Pedometer.stepCountStream.listen((event) async {
      if (_baseline == 0) {
        _baseline = event.steps;
      }
      _sessionSteps = (event.steps - _baseline).clamp(0, 999999);
      await onSync(_sessionSteps);
    }, onError: (_) => stop());
  }

  void stop() {
    _sub?.cancel();
    _sub = null;
    _running = false;
    _baseline = 0;
  }

  void dispose() => stop();
}
