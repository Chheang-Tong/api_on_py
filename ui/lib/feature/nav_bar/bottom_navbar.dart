import 'package:flutter/material.dart';
import 'package:flutter_svg/svg.dart';
import 'package:ui/appbar.dart';
import 'package:ui/feature/home/home.dart';
import 'package:ui/feature/profile/profile.dart';
import 'package:ui/feature/waiting/waiting.dart';

class BottomNavbars extends StatefulWidget {
  const BottomNavbars({super.key});

  @override
  State<BottomNavbars> createState() => _BottomNavbarsState();
}

class _BottomNavbarsState extends State<BottomNavbars> {
  int _selectedIndex = 0;
  late final PageController _pageController;

  static const List<Widget> _pages = <Widget>[
    HomeScreen(),
    Waiting(),
    Profile(),
  ];

  final List<String> _icons = const [
    'assets/icons/heart_beat.svg',
    'assets/icons/clock.svg',
    'assets/icons/user.svg',
  ];

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: _selectedIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _onTapNav(int i) {
    if (i == _selectedIndex) return;
    setState(() => _selectedIndex = i);
    _pageController.animateToPage(
      i,
      duration: const Duration(milliseconds: 350),
      curve: Curves.easeInOutCubic,
    );
  }

  @override
  Widget build(BuildContext context) {
    assert(_pages.length == _icons.length,
    'Pages and icons length must match');

    return Scaffold(
      extendBody: true,
      // appBar: CustomAppBar(actions: Icon(Icons.menu),),
      body: Stack(
        children: [

          PageView(
          controller: _pageController,
          physics: const BouncingScrollPhysics(),
          onPageChanged: (i) => setState(() => _selectedIndex = i),
          children: _pages,
        ),
          Positioned(
            top: 70,
            right: 10,
            child: Icon(Icons.menu),),
        ]
      ),
      bottomNavigationBar: _BottomBar(
        icons: _icons,
        selectedIndex: _selectedIndex,
        onTap: _onTapNav,
      ),
    );
  }
}

class _BottomBar extends StatelessWidget {
  const _BottomBar({
    required this.icons,
    required this.selectedIndex,
    required this.onTap,
  });

  final List<String> icons;
  final int selectedIndex;
  final ValueChanged<int> onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 90,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(20), topRight: Radius.circular(20),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -5),
          ),
        ],
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final segmentWidth = constraints.maxWidth / icons.length;
          const indicatorWidth = 36.0;
          final indicatorLeft = segmentWidth * selectedIndex +
              (segmentWidth - indicatorWidth) / 2;

          return Stack(
            alignment: Alignment.center,
            children: [
              // Sliding underline
              AnimatedPositioned(
                duration: const Duration(milliseconds: 300),
                curve: Curves.easeInOut,
                left: indicatorLeft,
                bottom: 20,
                child: Container(
                  width: indicatorWidth,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.blue,
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),

              // Icons
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: List.generate(icons.length, (i) {
                  final isActive = i == selectedIndex;
                  return GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: () => onTap(i),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        SvgPicture.asset(
                          icons[i],
                          width: 30,
                          height: 30,
                          color: isActive ? Colors.blue : Colors.grey,
                        ),
                        const SizedBox(height: 12),
                      ],
                    ),
                  );
                }),
              ),
            ],
          );
        },
      ),
    );
  }
}
