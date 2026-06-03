import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/constants.dart';

class PointsScreen extends StatefulWidget {
  const PointsScreen({super.key});

  @override
  State<PointsScreen> createState() => _PointsScreenState();
}

class _PointsScreenState extends State<PointsScreen> {
  int _balance = 0;
  List<dynamic> _ledger = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final client = await ApiClient.create();
      _balance = await client.balance();
      _ledger = await client.ledger();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Wellness points')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(wellnessDisclaimer, style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 12),
                Text('Balance: $_balance', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 16),
                const Text('Ledger (no redemption in Phase 1)'),
                ..._ledger.map(
                  (e) => ListTile(
                    title: Text(e['description'] ?? e['reason']),
                    trailing: Text('+${e['delta_points']}'),
                  ),
                ),
              ],
            ),
    );
  }
}
