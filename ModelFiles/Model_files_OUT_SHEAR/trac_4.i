[BCs]
  [./uz_yz_top]
    type = NeumannBC
    variable = u_z
    boundary = top
    value = 1
  [../]

  [./uz_yz_bottom]
    type = NeumannBC
    variable = u_z
    boundary = bottom
    value = -1
  [../]

  [./constraint]
    type = DirichletBC
    variable = u_z
    boundary = bottomleft
    value = 0
  [../]
[]
