[Physics]
  [SolidMechanics]
    [QuasiStatic]
      [./all]
        strain              = SMALL
        add_variables = true
      scalar_out_of_plane_strain = scalar_strain_z
        planar_formulation = GENERALIZED_PLANE_STRAIN
        generate_output    = 'stress_xx stress_yy stress_zz stress_xy strain_xx strain_yy strain_zz strain_xy'
      [../]
    [../]
  [../]
[]
