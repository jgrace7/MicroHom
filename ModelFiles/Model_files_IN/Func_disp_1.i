[Functions]
  [./ux_macro]
    type = ParsedFunction
    expression = '0.00 * (x - {{XC}})'
  [../]

  [./uy_macro]
    type = ParsedFunction
    expression = '0.01 * (y - {{YC}})'
  [../]
[]
