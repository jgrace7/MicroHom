[BCs]
  [./uz_xz_bc]
    type = FunctionNeumannBC
    variable = u_z
    boundary = 'left right'
    function = uz_macro_xz
  [../]

  [./uz_yz_bc]
    type = FunctionNeumannBC
    variable = u_z
    boundary = 'bottom top'
    function = uz_macro_yz
  [../]
[]
