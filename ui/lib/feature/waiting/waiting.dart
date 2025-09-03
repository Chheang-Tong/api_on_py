import 'dart:ui';

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
    return Scaffold(
      body: Stack(
        children: [
          Align(
            alignment: AlignmentDirectional(3.2, -0.3),
            child: Container(
                height: 300,
                width: 270,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.green,
                )),
          ),
          Align(
            alignment: AlignmentDirectional(-6, -0.4),
            child: Container(
                height: 390,
                width: 390,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.blue,
                )),
          ),
          Align(
            alignment: AlignmentDirectional(2, -1.2),
            child: Container(
              height: 300,
              width: 300,
              decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Color(0xFFFFAB40)),
            ),
          ),
          Align(
            alignment: AlignmentDirectional(-3.5, 1.1),
            child: Container(
                height: 380,
                width: 380,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.black,
                )),
          ),
          Align(
            alignment: AlignmentDirectional(2, 01),
            child: Container(
                height: 300,
                width: 300,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.black,
                )),
          ),
          BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 100.0, sigmaY: 100.0),
            child: Container(
              decoration: BoxDecoration(color: Colors.transparent),
            ),
          ),

        ],
      ));

  }
}
