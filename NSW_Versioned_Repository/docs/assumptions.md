# Causal assumptions

## Primary NSW experimental analysis

Let W contain recorded pretreatment variables, T be historical training
assignment, and Y be real earnings in 1978. The experimental DAG has
W → Y and T → Y, with factorization p(W)p(T)p(Y | W,T).

Under randomized assignment, there is no open back-door path from T to Y
in this DAG. The empty set is sufficient for identification. Baseline
adjustment is used to improve precision. The interpretation assumes
consistency and no interference between participants.

The hypothetical allocation decision D is distinct from historical
assignment T. The observed earnings reveal the outcome under the assigned
arm. An individual participant's treatment effect is unobserved.

## Observational sensitivity analysis

The observational DAG adds W → T, allowing the back-door path T ← W → Y.
Adjustment requires that measured pretreatment variables block the relevant
back-door paths and that comparable treated and control cases have overlap.
Post-training employment and earnings are excluded from adjustment.

The sensitivity simulation adds U → T and U → Y for an unmeasured common
cause. The strength and effects of U are simulated.

## Exact inference fixture

The discrete verification DAG uses G → X → Y and T → Y, where G is a
binary group indicator, X is a binary pretreatment earnings band, and
Y is a binary positive-earnings indicator. Its conditional probabilities
are constructed for verification. The NSW ATE uses the original continuous
earnings outcome.