import 'package:flutter/material.dart';

// ── Bold label above each form section ─────────────────────────
class SectionLabel extends StatelessWidget {
  const SectionLabel(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.bold,
        color: Color(0xFF1A1A1A),
      ),
    );
  }
}

// ── Tappable row that opens the calendar picker ─────────────────
class DateTile extends StatelessWidget {
  const DateTile({
    super.key,
    required this.date,
    required this.onTap,
    required this.color,
  });

  final DateTime? date;
  final VoidCallback onTap;
  final Color color;

  static String _fmt(DateTime d) {
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December',
    ];
    const weekdays = [
      'Monday', 'Tuesday', 'Wednesday',
      'Thursday', 'Friday', 'Saturday', 'Sunday',
    ];
    return '${weekdays[d.weekday - 1]}, ${months[d.month - 1]} ${d.day}';
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: date != null ? color : const Color(0xFFDDDDDD),
              width: date != null ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Icon(Icons.calendar_today_outlined, color: color, size: 20),
              const SizedBox(width: 12),
              Text(
                date != null ? _fmt(date!) : 'Choose a date…',
                style: TextStyle(
                  fontSize: 15,
                  color: date != null
                      ? const Color(0xFF1A1A1A)
                      : Colors.grey[400],
                  fontWeight:
                      date != null ? FontWeight.w500 : FontWeight.normal,
                ),
              ),
              const Spacer(),
              Icon(Icons.arrow_forward_ios, size: 14, color: Colors.grey[400]),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Horizontally scrollable time-slot pills ─────────────────────
class TimeChips extends StatelessWidget {
  const TimeChips({
    super.key,
    required this.slots,
    required this.selected,
    required this.onSelect,
    required this.color,
  });

  final List<String> slots;
  final String? selected;
  final ValueChanged<String> onSelect;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: slots.map((slot) {
          final active = slot == selected;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: GestureDetector(
              onTap: () => onSelect(slot),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 120),
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: active ? color : Colors.white,
                  borderRadius: BorderRadius.circular(30),
                  border: Border.all(
                    color: active ? color : const Color(0xFFDDDDDD),
                  ),
                ),
                child: Text(
                  slot,
                  style: TextStyle(
                    color: active ? Colors.white : Colors.black87,
                    fontWeight: FontWeight.w500,
                    fontSize: 13,
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ── Duration option pills displayed in a wrapping grid ──────────
// Pass options as a Map of {display label: hours}, e.g. {'2 hours': 2}
class DurationChips extends StatelessWidget {
  const DurationChips({
    super.key,
    required this.options,
    required this.selected,
    required this.onSelect,
    required this.color,
  });

  final Map<String, int> options;
  final int? selected;
  final ValueChanged<int> onSelect;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 10,
      runSpacing: 8,
      children: options.entries.map((e) {
        final active = selected == e.value;
        return GestureDetector(
          onTap: () => onSelect(e.value),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 120),
            padding:
                const EdgeInsets.symmetric(horizontal: 20, vertical: 11),
            decoration: BoxDecoration(
              color: active ? color : Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: active ? color : const Color(0xFFDDDDDD),
              ),
            ),
            child: Text(
              e.key,
              style: TextStyle(
                color: active ? Colors.white : Colors.black87,
                fontWeight: FontWeight.w600,
                fontSize: 14,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}

// ── +/− quantity counter (e.g. number of carts or people) ───────
class QuantityCounter extends StatelessWidget {
  const QuantityCounter({
    super.key,
    required this.value,
    required this.min,
    required this.max,
    required this.singularLabel,
    required this.pluralLabel,
    required this.icon,
    required this.color,
    required this.onChanged,
  });

  final int value;
  final int min;
  final int max;
  final String singularLabel;
  final String pluralLabel;
  final IconData icon;
  final Color color;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFDDDDDD)),
      ),
      child: Row(
        children: [
          Icon(icon, color: Colors.grey[500], size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              value == 1 ? '1 $singularLabel' : '$value $pluralLabel',
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
            ),
          ),
          _Btn(
            icon: Icons.remove,
            active: value > min,
            color: color,
            filled: false,
            onTap: () => onChanged(value - 1),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              '$value',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ),
          _Btn(
            icon: Icons.add,
            active: value < max,
            color: color,
            filled: true,
            onTap: () => onChanged(value + 1),
          ),
        ],
      ),
    );
  }
}

class _Btn extends StatelessWidget {
  const _Btn({
    required this.icon,
    required this.active,
    required this.color,
    required this.filled,
    required this.onTap,
  });
  final IconData icon;
  final bool active;
  final Color color;
  final bool filled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: active ? onTap : null,
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: active
              ? (filled ? color : color.withOpacity(0.1))
              : Colors.grey[100],
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(
          icon,
          size: 18,
          color: active
              ? (filled ? Colors.white : color)
              : Colors.grey[300],
        ),
      ),
    );
  }
}

// ── Price breakdown card shown before confirming ────────────────
class PriceSummaryCard extends StatelessWidget {
  const PriceSummaryCard({
    super.key,
    required this.lineItems,
    required this.total,
    required this.color,
  });

  // Each item is (description, amount string), e.g. ('2 carts × 3h × $25', '$150')
  final List<(String, String)> lineItems;
  final String total;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Price Summary',
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 13,
              letterSpacing: 0.3,
            ),
          ),
          const SizedBox(height: 12),
          ...lineItems.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(item.$1,
                      style:
                          TextStyle(color: Colors.grey[600], fontSize: 13)),
                  Text(item.$2, style: const TextStyle(fontSize: 13)),
                ],
              ),
            ),
          ),
          const Divider(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Total',
                  style:
                      TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              Text(
                total,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 22,
                  color: color,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
