  [./elasticity_{{PHASE}}]
    type = ComputeIsotropicElasticityTensor
    block = {{BLOCK}}
    youngs_modulus = {{E}}
    poissons_ratio = {{NU}}
  [../]
  
  [./eigen_{{PHASE}}]
    type             = ComputeEigenstrain
    block            = '{{BLOCK}}'
    eigen_base       =  '{{eig}}'
    prefactor        = 1
    eigenstrain_name = eigenstrain
  [../]

  [./stress_{{PHASE}}]
    type  = ComputeLinearElasticStress
    block = '{{BLOCK}}'
  [../]
