
import 'package:flutter/material.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget{
  final Widget? leading;
  final Widget? title;
  final Widget? actions;
  final Color? backgroundColor;
  final double height;
  const CustomAppBar({super.key,
    this.leading,
    this.title,
    this.actions,
    this.backgroundColor,
    this.height=kToolbarHeight,
  });

  @override
  Widget build(BuildContext context) {
    return AppBar(
      elevation: 0,
      backgroundColor: backgroundColor??Theme.of(context).appBarTheme.backgroundColor,
      automaticallyImplyLeading: false,
      titleSpacing: 0,
      title: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: [
            if(leading !=null)leading!,
            if(title!=null)Expanded(child: title!)else Spacer(),
            if(actions!=null)actions!
          ],),
      ),
    );

  }

  @override
  Size get preferredSize => Size.fromHeight(height);
}