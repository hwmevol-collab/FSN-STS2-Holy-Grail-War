# NATIVE_UI_FIRST_FOR_PUBLIC_PATH

Confirmed target: v0.0.0.0.1 Steam Workshop Public Vertical Slice.

For STS2 base interfaces that players must use in the normal flow, first extend or reuse native STS2 UI: native cards, hover/input, buttons, controller/navigation, layout and scaling. Development windows may support QA. If a native extension cannot be made safely, document the architecture investigation and propose the smallest native-compatible solution before replacing it with a custom window.

D1 adds only two reward stages, `1 / 2 · MASTER — 远坂凛` and `2 / 2 · SERVANT — Archer`, with the necessary owner/HP hints. Development IDs may remain. Official FSN art, final card frames and Voice/VFX remain outside the current authorized scope. D2 adds only the authorized campfire, merchant and card services described below. This policy does not authorize gameplay, numerical or Dual Reward rule changes.

`D1_QA_MAP_SPARSITY = EXPECTED_NON_BLOCKING`: the existing three encounter topology is a constrained QA route. Do not fill the map or add hardcoded spacing. Return to complete native Act generation only after the later campfire/merchant/event/elite/boss work is supported and authorized.

Combat victory shows the native Combat Reward container. It owns Gold and all other native items; one Card Reward item opens Master then Servant, and completion resolves that item and returns to the same container. Fresh victories never automatically open card selection. Native Continue may resume an already-started Servant stage with its saved offer.

`PUBLIC_UI_MODE`: normal D1 entry defaults to a minimal gameplay HUD, with large debug information and QA-only controls hidden. Explicit QA entries retain the full HUD and helpers. F8 toggles the development overlay; public-mode helpers remain hidden. Telemetry is retained. The QA Save/Exit reward alternative is absent from public Card Reward screens; public exits use native Pause / Save and Quit / Continue.

D2 uses native RestSiteRoom / HealRestSiteOption / SmithRestSiteOption, native popup buttons and confirmation, native deck upgrade/removal selection screens, and native MerchantRoom / MerchantInventory / slots. The selector adds two Owner tabs and shares a single target budget. Shop Owner labels sit above the four native cards. Native mouse/controller focus, card preview, cancel, scrolling, prices and save/continue remain the public path.

`QA_D2_RUN` scopes 30/10 Focus Rest, dual-deck Smith, 2+2 own-Alpha offers and one shared removal service. Inventory identity uses the Act and native map coordinate so native non-combat reconstruction cannot reset a room service. Relic/potion/colorless eligibility is suppressed only in this QA capability; the complete native subsystems remain available in vanilla. The constrained native QA route adds one second merchant to verify global 75→100 removal pricing. It adds 500 fixture Gold independently of character StartingGold and carries `NOT_PUBLIC_BALANCE` / `NOT_PUBLIC_FINAL_RUN`.

D2 completes engineering checks first, then waits for the user to play the flow and provide feedback. Physical controller testing remains deferred to Workshop RC. This policy does not authorize Milestone E, balance changes, events, full-map work, Command Spell, UBW or formal FSN assets.
