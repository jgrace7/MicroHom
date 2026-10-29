[Functions]
  [./ux_macro]
    type = ParsedFunction
    expression = '1.0 * (y - {{YC}})'
  [../]

  [./uy_macro]
    type = ParsedFunction
    expression = '1.0 * (x - {{XC}})'
  [../]
[]
