import 'package:flutter/material.dart';
import '../widgets/booking_widgets.dart';
import 'confirmation_screen.dart';

class GolfCartScreen extends StatefulWidget {
  const GolfCartScreen({super.key});

  @override
  State<GolfCartScreen> createState() => _GolfCartScreenState();
}

class _GolfCartScreenState extends State<GolfCartScreen> {
  static const Color _accent = Color(0xFF1B5E20);

  static const _timeSlots = [
    '8:00 AM', '9:00 AM', '10:00 AM', '11:00 AM',
    '12:00 PM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM', '5:00 PM',
  ];

  // Duration options shown to the user: label → number of hours
  static const Map<String, int> _durations = {
    '1 hour': 1,
    '2 hours': 2,
    '3 hours': 3,
    '4 hours': 4,
  };

  DateTime? _date;
  String? _time;
  int? _durationHours;
  int _carts = 1;

  // Price: $25 per cart per hour
  int get _price => (_durationHours ?? 0) * _carts * 25;

  // All required fields have been filled in
  bool get _ready =>
      _date != null && _time != null && _durationHours != null;

  // Look up the display label from the number of hours
  String get _durationLabel => _durations.entries
      .firstWhere((e) => e.value == _durationHours)
      .key;

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 1)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 90)),
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(
          colorScheme: const ColorScheme.light(primary: _accent),
        ),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _date = picked);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF2F2F2),
      appBar: AppBar(
        backgroundColor: _accent,
        foregroundColor: Colors.white,
        title: const Text('Golf Cart Rental'),
        elevation: 0,
      ),
      body: Column(
        children: [
          // Coloured sub-header with icon + pricing hint
          Container(
            color: _accent,
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
            child: Row(
              children: [
                const Icon(Icons.electric_rickshaw,
                    color: Colors.white, size: 36),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Reserve Your Cart',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '\$25 per cart · per hour',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.8),
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SectionLabel('Date'),
                  const SizedBox(height: 8),
                  DateTile(date: _date, onTap: _pickDate, color: _accent),
                  const SizedBox(height: 24),

                  const SectionLabel('Start Time'),
                  const SizedBox(height: 10),
                  TimeChips(
                    slots: _timeSlots,
                    selected: _time,
                    onSelect: (t) => setState(() => _time = t),
                    color: _accent,
                  ),
                  const SizedBox(height: 24),

                  const SectionLabel('Duration'),
                  const SizedBox(height: 10),
                  DurationChips(
                    options: _durations,
                    selected: _durationHours,
                    onSelect: (h) => setState(() => _durationHours = h),
                    color: _accent,
                  ),
                  const SizedBox(height: 24),

                  const SectionLabel('Number of Carts'),
                  const SizedBox(height: 10),
                  QuantityCounter(
                    value: _carts,
                    min: 1,
                    max: 4,
                    singularLabel: 'cart',
                    pluralLabel: 'carts',
                    icon: Icons.electric_rickshaw,
                    color: _accent,
                    onChanged: (n) => setState(() => _carts = n),
                  ),
                  const SizedBox(height: 24),

                  // Price summary only appears once all fields are filled
                  if (_ready)
                    PriceSummaryCard(
                      lineItems: [
                        (
                          '$_carts cart${_carts > 1 ? 's' : ''} × '
                              '$_durationHours h × \$25',
                          '\$$_price',
                        ),
                      ],
                      total: '\$$_price',
                      color: _accent,
                    ),

                  const SizedBox(height: 80),
                ],
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
          child: ElevatedButton(
            onPressed: _ready
                ? () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => ConfirmationScreen(
                          rentalType: 'Golf Cart',
                          icon: Icons.electric_rickshaw,
                          accentColor: _accent,
                          date: _date!,
                          time: _time!,
                          durationLabel: _durationLabel,
                          quantityLabel:
                              '$_carts cart${_carts > 1 ? 's' : ''}',
                          totalPrice: _price,
                        ),
                      ),
                    )
                : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: _accent,
              foregroundColor: Colors.white,
              disabledBackgroundColor: Colors.grey[300],
              minimumSize: const Size(double.infinity, 54),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14)),
            ),
            child: Text(
              _ready ? 'Confirm Booking — \$$_price' : 'Fill in all fields to continue',
              style: const TextStyle(
                  fontSize: 15, fontWeight: FontWeight.bold),
            ),
          ),
        ),
      ),
    );
  }
}
