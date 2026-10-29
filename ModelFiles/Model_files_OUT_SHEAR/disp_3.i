[BCs]
  [./uz_xz_bc]
    type = FunctionDirichletBC
    variable = u_z
    boundary = 'left right top bottom'
    function = uz_macro_xz
  [../]
[]
