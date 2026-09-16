# Public Worker Placement repository

Worker Placement is the family-office product. OfficeKit powers the app and SignalOS provides its research and evidence.

This repository begins with one initial commit from the published product snapshot reviewed on 2026-09-16. It is a separate repository, not a fork or mirror of the private development repository. Existing private Git history is not included.

The snapshot retains the source, position history, and research datasets. Confirmed brokerage account identifiers use consistent anonymous labels. The bundled historical data is reference material; new users create their own office with `./start.sh`. Runtime account connections and provider credentials belong in private local configuration.

## Contributing safely

Use `main` in `AjayTripathy/worker-placement`. Do not add the private development repository as an upstream and merge its history. Transfer reviewed source changes as patches, keeping private office files, account identifiers, authentication material, and runtime credentials out of commits.

The installer, hosted landing page, and local guide use this public repository. The startup folder is `worker-placement`; run `./start.sh`, `./wp login`, and `./wp migrate` there. Research datasets are included in a normal clone.

Public visibility alone does not change third-party source terms. Retained research preserves its existing source provenance and dates.
