[BCs]
  [./uz_disp_xz]
    type = FunctionDirichletBC
    variable = u_z
    boundary = 'left right'
    function = uz_macro_xz
  [../]

  [./uz_trac_yz]
    type = NeumannBC
    variable = u_z
    boundary = 'top bottom'
    value = 0
  [../]
[]
