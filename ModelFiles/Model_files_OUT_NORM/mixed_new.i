[BCs]
  [./top_y]
    type     = DirichletBC
    variable = disp_y
    boundary = 'top'
    value    = 0
  [../]

  [./bottom_y]
    type     = DirichletBC
    variable = disp_y
    boundary = 'bottom'
    value    = 0
  [../]

  [./left_x]
    type     = DirichletBC
    variable = disp_x
    boundary = 'left'
    value    = 0
  [../]

  [./right_x]
    type     = DirichletBC
    variable = disp_x
    boundary = 'right'
    value    = 0
  [../]

  [./fix_z_strain]
    type = ScalarDirichletBC
    variable = scalar_strain_z
    value = 0.01
  [../]
[]