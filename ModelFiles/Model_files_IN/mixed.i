[BCs]
  [./ux_disp]
    type = FunctionDirichletBC
    variable = disp_x
    boundary = 'left right'
    function = ux_macro
  [../]

  [./uy_disp]
    type = FunctionDirichletBC
    variable = disp_y
    boundary = 'bottom top'
    function = uy_macro
  [../]
[]
