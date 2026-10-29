[Functions]
  [./ux_macro]
    type = ParsedFunction
    expression = '0.005 * (y - {{YC}})'
  [../]

  [./uy_macro]
    type = ParsedFunction
    expression = '0.005 * (x - {{XC}})'
  [../]
[]
