import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:lottie/lottie.dart';
import '../../appbar.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  Widget build(BuildContext context) {
    Size size=MediaQuery.of(context).size;
    const gradient = LinearGradient(
      colors: [Color(0xFF4FACFE), Color(0xFF00F2FE)],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    );

    return Scaffold(
      appBar: const CustomAppBar(
        title: Text('Daily Goal'),
        // actions: Icon(Icons.menu),
      ),
      body: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: SingleChildScrollView(
          child: Column(
            children: [
              // Pretty 87%
              Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: const [
                  GradientText(
                    '87',
                    gradient: gradient,
                    style: TextStyle(
                      fontSize: 72,
                      fontWeight: FontWeight.w600,
                      height: 0.9,
                      letterSpacing: -2,
                      shadows: [
                        Shadow(
                          offset: Offset(0, 2),
                          blurRadius: 8,
                          color: Color(0x33000000), // subtle glow
                        ),
                      ],
                    ),
                  ),
                  SizedBox(width: 6),
                  GradientText(
                    '%',
                    gradient: gradient,
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5,
                      shadows: [
                        Shadow(
                          offset: Offset(0, 1),
                          blurRadius: 4,
                          color: Color(0x22000000),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 100,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        iconRow(icon: SvgPicture.asset('assets/icons/fire.svg',width: 30,), title: "1,840", subTitle: "calories"),
                        iconRow(icon: SvgPicture.asset('assets/icons/shoe.svg',width: 30,color: Colors.blue,), title: "1,840", subTitle: "calories"),
                        iconRow(icon: SvgPicture.asset('assets/icons/moon.svg',width: 30,color: Colors.green,), title: "1,840", subTitle: "calories"),
          
                      ],
                    ),
                  ),
                  Expanded(
                    child: Lottie.asset('assets/animation/runner.json'),
                  ),
                ],
              ),
              Container(
                width: size.width,
                height: 80,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  color: Colors.green
                ),
                child: Row(
                  children: [

                  ],
                ),
              )
            ],
          ),
        ),
      ),
    );
  }
  Widget iconRow({
    required Widget icon,
    required String title,
    required String subTitle,
    }){
    return Row(
      children: [
        Padding(
          padding: const EdgeInsets.all(4.0),
          child: icon,
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title),
            Text(subTitle)
          ],
        ),
      ],
    );
  }
}

class GradientText extends StatelessWidget {
  const GradientText(
      this.text, {
        super.key,
        required this.gradient,
        required this.style,
      });

  final String text;
  final Gradient gradient;
  final TextStyle style;

  @override
  Widget build(BuildContext context) {
    return ShaderMask(
      blendMode: BlendMode.srcIn,
      shaderCallback: (bounds) =>
          gradient.createShader(Rect.fromLTWH(0, 0, bounds.width, bounds.height)),
      child: Text(text, style: style.copyWith(color: Colors.white)),
    );
  }
}
