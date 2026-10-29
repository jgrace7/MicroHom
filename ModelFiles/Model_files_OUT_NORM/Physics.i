[Physics]
  [SolidMechanics]
    [QuasiStatic]
      [./all]
        strain              = SMALL
        add_variables = true
        eigenstrain_names  = 'eigenstrain'
        generate_output = 'stress_xx stress_yy stress_zz stress_xy stress_xz stress_yz strain_xx strain_yy strain_zz strain_xy strain_xz strain_yz'
      [../]
    [../]
  [../]
[]
