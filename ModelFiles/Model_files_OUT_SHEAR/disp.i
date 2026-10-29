[BCs]
  [./uz_xz_bc]
    type = FunctionDirichletBC
    variable = u_z
    boundary = 'left right'
    function = uz_macro_xz
  [../]

  [./uz_yz_bc]
    type = FunctionDirichletBC
    variable = u_z
    boundary = 'bottom top'
    function = uz_macro_yz
  [../]
[]
