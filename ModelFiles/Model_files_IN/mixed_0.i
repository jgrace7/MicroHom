[BCs]
  [./ux]
    type = FunctionDirichletBC
    variable = disp_x
    boundary = 'left right'
    function = ux_macro
  [../]

  [./uy]
    type = DirichletBC
    variable = disp_y
    boundary = 'top bottom'
    value = 0
  [../]
[]
