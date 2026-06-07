import 'package:flutter/material.dart';
import '../widgets/booking_widgets.dart';
import 'confirmation_screen.dart';

class SaunaScreen extends StatefulWidget {
  const SaunaScreen({super.key});

  @override
  State<SaunaScreen> createState() => _SaunaScreenState();
}

class _SaunaScreenState extends State<SaunaScreen> {
  static const Color _accent = Color(0xFFBF360C);

  static const _timeSlots = [
    '8:00 AM', '9:00 AM', '10:00 AM', '11:00 AM',
    '12:00 PM', '1:00 PM', '2:00 PM', '3:00 PM',
    '4:00 PM', '5:00 PM', '6:00 PM', '7:00 PM',
  ];

  static const Map<String, int> _durations = {
    '1 hour': 1,
    '2 hours': 2,
    '3 hours': 3,
  };

  DateTime? _date;
  String? _time;
  int? _durationHours;
  int _people = 2;

  // Price: $30 per hour flat (whole sauna, regardless of group size)
  int get _price => (_durationHours ?? 0) * 30;

  bool get _ready =>
      _date != null && _time != null && _durationHours != null;

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
        title: const Text('Sauna Rental'),
        elevation: 0,
      ),
      body: Column(
        children: [
          Container(
            color: _accent,
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
            child: Row(
              children: [
                const Icon(Icons.local_fire_department,
                    color: Colors.white, size: 36),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Reserve the Sauna',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '\$30 per hour · whole sauna',
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

                  const SectionLabel('Number of People'),
                  const SizedBox(height: 10),
                  QuantityCounter(
                    value: _people,
                    min: 1,
                    max: 8,
                    singularLabel: 'person',
                    pluralLabel: 'people',
                    icon: Icons.people_outline,
                    color: _accent,
                    onChanged: (n) => setState(() => _people = n),
                  ),
                  const SizedBox(height: 6),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Text(
                      'The entire sauna is reserved exclusively for your group.',
                      style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                    ),
                  ),
                  const SizedBox(height: 24),

                  if (_ready)
                    PriceSummaryCard(
                      lineItems: [
                        (
                          '$_durationHours hour${_durationHours! > 1 ? 's' : ''} × \$30',
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
                          rentalType: 'Sauna',
                          icon: Icons.local_fire_department,
                          accentColor: _accent,
                          date: _date!,
                          time: _time!,
                          durationLabel: _durationLabel,
                          quantityLabel:
                              '$_people ${_people == 1 ? 'person' : 'people'}',
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
