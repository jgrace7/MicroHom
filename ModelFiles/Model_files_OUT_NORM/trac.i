[BCs]
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