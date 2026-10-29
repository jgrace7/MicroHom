[BCs]
  [./ux_all]
    type = FunctionDirichletBC
    variable = disp_x
    boundary = 'left right top bottom'
    function = ux_macro
  [../]

  [./uy_all]
    type = FunctionDirichletBC
    variable = disp_y
    boundary = 'left right top bottom'
    function = uy_macro
  [../]
[]


