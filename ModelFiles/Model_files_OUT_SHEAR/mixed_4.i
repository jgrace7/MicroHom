[BCs]
  [./uz_disp_yz]
    type = FunctionDirichletBC
    variable = u_z
    boundary = 'top bottom'
    function = uz_macro_yz
  [../]

  [./uz_trac_xz]
    type = NeumannBC
    variable = u_z
    boundary = 'left right'
    value = 0
  [../]
[]