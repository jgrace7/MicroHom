[BCs]
  [./uz_disp_xz]
    type = FunctionDirichletBC
    variable = u_z
    boundary = 'left right'
    function = uz_macro_xz
  [../]

  [./uz_disp_yz]
    type = FunctionDirichletBC
    variable = u_z
    boundary = 'bottom top'
    function = uz_macro_yz
  [../]
[]
