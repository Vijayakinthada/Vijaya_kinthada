import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/constants.dart';

class VitalsScreen extends StatefulWidget {
  const VitalsScreen({super.key, required this.onSaved});

  final VoidCallback onSaved;

  @override
  State<VitalsScreen> createState() => _VitalsScreenState();
}

class _VitalsScreenState extends State<VitalsScreen> {
  final _systolicController = TextEditingController();
  final _diastolicController = TextEditingController();
  final _pulseController = TextEditingController();
  final _moodController = TextEditingController();
  final _sleepController = TextEditingController();
  bool _saving = false;
  String? _reviewMessage;

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final client = await ApiClient.create();
      final today = DateFormat('yyyy-MM-dd').format(DateTime.now());
      final result = await client.upsertVitals(
        today,
        bpSystolic: int.tryParse(_systolicController.text),
        bpDiastolic: int.tryParse(_diastolicController.text),
        pulse: int.tryParse(_pulseController.text),
        mood: int.tryParse(_moodController.text),
        sleepHours: double.tryParse(_sleepController.text),
      );
      setState(() {
        _reviewMessage = result['review_message'] as String?;
      });
      widget.onSaved();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Vitals saved')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('BP & pulse')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(wellnessDisclaimer, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 16),
            TextField(
              controller: _systolicController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Systolic BP',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _diastolicController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Diastolic BP',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _pulseController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Pulse',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _moodController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Mood (1–5, optional)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _sleepController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Sleep hours (optional)',
                border: OutlineInputBorder(),
              ),
            ),
            if (_reviewMessage != null) ...[
              const SizedBox(height: 16),
              MaterialBanner(
                content: Text(_reviewMessage!),
                backgroundColor: Colors.amber.shade50,
                actions: [
                  TextButton(
                    onPressed: () =>
                        ScaffoldMessenger.of(context).hideCurrentMaterialBanner(),
                    child: const Text('Dismiss'),
                  ),
                ],
              ),
            ],
            const Spacer(),
            FilledButton(
              onPressed: _saving ? null : _save,
              child: const Text('Save vitals'),
            ),
          ],
        ),
      ),
    );
  }
}
