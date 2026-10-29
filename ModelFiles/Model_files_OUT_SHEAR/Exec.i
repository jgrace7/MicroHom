[Executioner]
  type = Steady

  solve_type = NEWTON

  nl_rel_tol = 1e-10
  nl_abs_tol = 1e-12

  l_tol = 1e-10
  l_abs_tol = 1e-12

  line_search = none

  petsc_options_iname = '
    -ksp_type
    -pc_type
    -pc_factor_mat_solver_type
  '

  petsc_options_value = '
    preonly
    lu
    mumps
  '
[]
