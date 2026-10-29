[BCs]
  [./ux_all]
    type     = DirichletBC
    variable = disp_x
    boundary = 'left right top bottom'
    value    = 0
  [../]

  [./uy_all]
    type     = DirichletBC
    variable = disp_y
    boundary = 'left right top bottom'
    value    = 0
  [../]
[]