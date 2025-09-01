import 'package:flutter/material.dart';
import 'package:flutter_svg/svg.dart';
class Waiting extends StatefulWidget {
  const Waiting({super.key});

  @override
  State<Waiting> createState() => _WaitingState();
}

class _WaitingState extends State<Waiting> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(appBar: AppBar(title: const Text('Home Screen'),),body: Center(child: SvgPicture.asset("assets/icons/clock.svg"),),);

  }
}
