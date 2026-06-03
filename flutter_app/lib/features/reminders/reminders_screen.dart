import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/constants.dart';

class RemindersScreen extends StatefulWidget {
  const RemindersScreen({super.key, required this.onSaved});

  final VoidCallback onSaved;

  @override
  State<RemindersScreen> createState() => _RemindersScreenState();
}

class _RemindersScreenState extends State<RemindersScreen> {
  bool _enabled = true;
  final _walkTimeController = TextEditingController(text: '09:00');
  final _vitalsTimeController = TextEditingController(text: '20:00');
  bool _saving = false;

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final client = await ApiClient.create();
      await client.upsertReminders(
        enabled: _enabled,
        walkReminderTime: _walkTimeController.text,
        vitalsReminderTime: _vitalsTimeController.text,
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
      appBar: AppBar(title: const Text('Reminders')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(wellnessDisclaimer, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 16),
            SwitchListTile(
              title: const Text('Enable reminders'),
              value: _enabled,
              onChanged: (v) => setState(() => _enabled = v),
            ),
            TextField(
              controller: _walkTimeController,
              decoration: const InputDecoration(
                labelText: 'Walk reminder (HH:MM)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _vitalsTimeController,
              decoration: const InputDecoration(
                labelText: 'Vitals reminder (HH:MM)',
                border: OutlineInputBorder(),
              ),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _saving ? null : _save,
              child: const Text('Save reminders'),
            ),
          ],
        ),
      ),
    );
  }
}
