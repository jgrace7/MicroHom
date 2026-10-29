[BCs]
  [./t22_top]
    type = NeumannBC
    variable = disp_y
    boundary = top
    value = 1
  [../]

  [./t22_bottom]
    type = NeumannBC
    variable = disp_y
    boundary = bottom
    value = -1
  [../]

  [./t11]
    type = NeumannBC
    variable = disp_x
    boundary = 'left right'
    value = 0
  [../]

  [./constraint_1_x]
    type = DirichletBC
    variable = disp_x
    boundary = bottomleft
    value = 0
  [../]

  [./constraint_1_y]
    type = DirichletBC
    variable = disp_y
    boundary = bottomleft
    value = 0
  [../]

  [./constraint_2_y]
    type = DirichletBC
    variable = disp_y
    boundary = bottomright
    value = 0
  [../]
[]