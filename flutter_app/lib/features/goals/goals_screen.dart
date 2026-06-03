import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/constants.dart';

class GoalsScreen extends StatefulWidget {
  const GoalsScreen({super.key, required this.onSaved});

  final VoidCallback onSaved;

  @override
  State<GoalsScreen> createState() => _GoalsScreenState();
}

class _GoalsScreenState extends State<GoalsScreen> {
  final _stepsController = TextEditingController(text: '5000');
  final _minutesController = TextEditingController(text: '30');
  bool _saving = false;

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final client = await ApiClient.create();
      await client.upsertGoals(
        dailyStepTarget: int.parse(_stepsController.text),
        dailyActiveMinutesTarget: int.parse(_minutesController.text),
      );
      widget.onSaved();
      if (mounted) Navigator.pop(context);
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
      appBar: AppBar(title: const Text('Daily goals')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(wellnessDisclaimer, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 16),
            TextField(
              controller: _stepsController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Daily step target',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _minutesController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Daily active minutes target',
                border: OutlineInputBorder(),
              ),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _saving ? null : _save,
              child: const Text('Save goals'),
            ),
          ],
        ),
      ),
    );
  }
}
