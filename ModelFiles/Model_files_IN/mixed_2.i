[BCs]
  [./ux_disp]
    type = FunctionDirichletBC
    variable = disp_x
    boundary = 'bottom top'
    function = ux_macro
  [../]

  [./uy_disp]
    type = FunctionDirichletBC
    variable = disp_y
    boundary = 'left right'
    function = uy_macro
  [../]
[]
