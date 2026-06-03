import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/constants.dart';

/// Exchange history — reference: ExchangesHistoryPage + ExchangesItem.
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<dynamic> _items = [];
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
      _items = await client.history();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _formatDate(String? timestamp) {
    if (timestamp == null) return '';
    try {
      return DateFormat.yMMMd().format(DateTime.parse(timestamp));
    } catch (_) {
      return timestamp;
    }
  }

  IconData _iconForKind(String? kind) {
    switch (kind) {
      case 'ledger':
        return Icons.swap_horiz;
      case 'steps':
        return Icons.directions_walk;
      case 'session':
        return Icons.self_improvement;
      case 'vitals':
        return Icons.favorite_outline;
      default:
        return Icons.history;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Exchanges & history')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _items.isEmpty
              ? Center(
                  child: Text(
                    'No activity yet — walk to earn wellness points.',
                    style: Theme.of(context).textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: _items.length + 1,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      if (index == 0) {
                        return Padding(
                          padding: const EdgeInsets.all(16),
                          child: Text(
                            wellnessDisclaimer,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        );
                      }
                      final item = _items[index - 1];
                      final points = item['points_delta'];
                      final title = item['title'] as String? ?? '';
                      final displayTitle = points != null
                          ? '+$points wellness points — $title'
                          : title;

                      return ListTile(
                        leading: Icon(_iconForKind(item['kind'] as String?)),
                        title: Text(
                          displayTitle,
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        subtitle: Text(
                          '${item['detail'] ?? ''}\n${_formatDate(item['timestamp'] as String?)}',
                        ),
                        isThreeLine: true,
                      );
                    },
                  ),
                ),
    );
  }
}
