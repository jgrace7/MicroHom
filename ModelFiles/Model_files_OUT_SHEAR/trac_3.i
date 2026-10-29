[BCs]
  [./uz_xz_right]
    type = NeumannBC
    variable = u_z
    boundary = right
    value = 1
  [../]

  [./uz_xz_left]
    type = NeumannBC
    variable = u_z
    boundary = left
    value = -1
  [../]

  [./constraint]
    type = DirichletBC
    variable = u_z
    boundary = bottomleft
    value = 0
  [../]
[]
