[Functions]
  [./uz_macro_xz]
    type = ParsedFunction
    expression = '0.01 * (x - {{XC}})'
  [../]

  [./uz_macro_yz]
    type = ParsedFunction
    expression = '0.00 * (y - {{YC}})'
  [../]
[]
