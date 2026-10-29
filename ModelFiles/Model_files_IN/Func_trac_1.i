[Functions]
  [./ux_macro]
    type = ParsedFunction
    expression = '0.00 * (x - {{XC}})'
  [../]

  [./uy_macro]
    type = ParsedFunction
    expression = '1.0 * (y - {{YC}})'
  [../]
[]
