import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/constants.dart';

class LogSessionScreen extends StatefulWidget {
  const LogSessionScreen({super.key, required this.onSaved});

  final VoidCallback onSaved;

  @override
  State<LogSessionScreen> createState() => _LogSessionScreenState();
}

class _LogSessionScreenState extends State<LogSessionScreen> {
  String _type = gentleSessionTypes.first;
  final _minutesController = TextEditingController(text: '15');
  final _notesController = TextEditingController();
  bool _saving = false;

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final client = await ApiClient.create();
      final result = await client.logSession(
        sessionType: _type,
        durationMinutes: int.parse(_minutesController.text),
        startedAt: DateTime.now(),
        notes: _notesController.text.isEmpty ? null : _notesController.text,
      );
      final awarded = result['points_awarded'] as List<dynamic>? ?? [];
      if (mounted) {
        final total = awarded.fold<int>(
          0,
          (sum, e) => sum + (e['delta_points'] as num).toInt(),
        );
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Session saved · +$total points')),
        );
        widget.onSaved();
        Navigator.pop(context);
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
      appBar: AppBar(title: const Text('Log gentle session')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(wellnessDisclaimer, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _type,
              decoration: const InputDecoration(
                labelText: 'Wellness session type',
                border: OutlineInputBorder(),
              ),
              items: gentleSessionTypes
                  .map((t) => DropdownMenuItem(
                        value: t,
                        child: Text(t.replaceAll('_', ' ')),
                      ))
                  .toList(),
              onChanged: (v) => setState(() => _type = v!),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _minutesController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Duration (minutes)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _notesController,
              decoration: const InputDecoration(
                labelText: 'Notes (optional)',
                border: OutlineInputBorder(),
              ),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _saving ? null : _save,
              child: Text(_saving ? 'Saving…' : 'Save session'),
            ),
          ],
        ),
      ),
    );
  }
}
