// Optional reference root-item properties. Insert after Kirigami.Theme.inherit: false
// in the EXACT reviewed Breeze-derived Main.qml, then test before activation.
Kirigami.Theme.backgroundColor: config.noctaliaSurface || "#1f1f1f"
Kirigami.Theme.alternateBackgroundColor: config.noctaliaSurfaceVariant || "#292929"
Kirigami.Theme.textColor: config.noctaliaText || "#eeeeee"
Kirigami.Theme.highlightColor: config.noctaliaPrimary || "#dddddd"
Kirigami.Theme.highlightedTextColor: config.noctaliaOnPrimary || "#181818"
Kirigami.Theme.focusColor: config.noctaliaPrimary || "#dddddd"
Kirigami.Theme.hoverColor: config.noctaliaPrimary || "#dddddd"
Kirigami.Theme.linkColor: config.noctaliaPrimary || "#dddddd"
