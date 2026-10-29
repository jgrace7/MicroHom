[BCs]
  [./uy]
    type = FunctionDirichletBC
    variable = disp_y
    boundary = 'top bottom'
    function = uy_macro
  [../]

  [./ux]
    type = DirichletBC
    variable = disp_x
    boundary = 'right left'
    value = 0
  [../]
[]
