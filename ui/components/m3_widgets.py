"""
ui/components/m3_widgets.py
─────────────────────────────────────────────────────────────────────────────
Custom CTk widgets that replicate Material 3 component specs from the
Ploxt app:

  • M3Card             — surface-container card with large corner radius
  • M3FilledButton    — primary colour filled button (md.sys.color.primary)
  • M3TonalButton     — secondary-tonal button
  • M3OutlinedButton  — outlined button
  • M3TextField       — text field with outline and floating label feel
  • M3ProgressBar     — linear progress indicator (rounded ends)
  • M3Chip            — filter / choice chip
  • M3NavRail         — left navigation rail (desktop equivalent of BottomNav)
  • M3Divider         — 1-dp horizontal rule in outline colour
  • M3StatusBadge     — small coloured pill for status labels
"""

from __future__ import annotations
import customtkinter as ctk
from core.theme import ThemeManager, Shape, TypeScale


# ─────────────────────────────── M3Card ──────────────────────────────────────

class M3Card(ctk.CTkFrame):
    """
    Filled card — uses surface_container as background, large corner radius.
    Drop in as a container; add child widgets to it normally.
    """
    def __init__(self, master, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("corner_radius", Shape.large)
        kwargs.setdefault("fg_color", s.surface_container)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)


class M3OutlinedCard(ctk.CTkFrame):
    """Card variant with a subtle 1-px border."""
    def __init__(self, master, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("corner_radius", Shape.large)
        kwargs.setdefault("fg_color", s.surface_container)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", s.outline_variant)
        super().__init__(master, **kwargs)


# ─────────────────────────────── Buttons ─────────────────────────────────────

class M3FilledButton(ctk.CTkButton):
    """
    MD3 Filled Button.
    On-primary text, primary background, extra-large corner radius (pill shape).
    """
    def __init__(self, master, text: str = "", **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("corner_radius", Shape.extra_large)
        kwargs.setdefault("fg_color", s.primary)
        kwargs.setdefault("hover_color", s.primary_container)
        kwargs.setdefault("text_color", s.on_primary)
        kwargs.setdefault("font", ctk.CTkFont(*TypeScale.label_large))
        kwargs.setdefault("height", 40)
        super().__init__(master, text=text, **kwargs)


class M3TonalButton(ctk.CTkButton):
    """
    MD3 Filled Tonal Button.
    Secondary-container background.
    """
    def __init__(self, master, text: str = "", **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("corner_radius", Shape.extra_large)
        kwargs.setdefault("fg_color", s.secondary_cont)
        kwargs.setdefault("hover_color", s.secondary)
        kwargs.setdefault("text_color", s.on_secondary_cont)
        kwargs.setdefault("font", ctk.CTkFont(*TypeScale.label_large))
        kwargs.setdefault("height", 40)
        super().__init__(master, text=text, **kwargs)


class M3OutlinedButton(ctk.CTkButton):
    """
    MD3 Outlined Button.
    Transparent background with outline border.
    """
    def __init__(self, master, text: str = "", **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("corner_radius", Shape.extra_large)
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("hover_color", s.surface_variant)
        kwargs.setdefault("text_color", s.primary)
        kwargs.setdefault("border_color", s.outline)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("font", ctk.CTkFont(*TypeScale.label_large))
        kwargs.setdefault("height", 40)
        super().__init__(master, text=text, **kwargs)


class M3IconButton(ctk.CTkButton):
    """
    Square icon-only button. Pass text="" and use an image.
    """
    def __init__(self, master, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("corner_radius", Shape.full)
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("hover_color", s.surface_variant)
        kwargs.setdefault("text_color", s.on_surface)
        kwargs.setdefault("width", 40)
        kwargs.setdefault("height", 40)
        super().__init__(master, **kwargs)


# ─────────────────────────────── TextField ───────────────────────────────────

class M3TextField(ctk.CTkEntry):
    """
    Outlined text field mimicking MD3 OutlinedTextField.
    """
    def __init__(self, master, placeholder: str = "", **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("corner_radius", Shape.small)
        kwargs.setdefault("fg_color", s.surface_variant)
        kwargs.setdefault("border_color", s.outline)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("text_color", s.on_surface)
        kwargs.setdefault("placeholder_text_color", s.on_surface_var)
        kwargs.setdefault("font", ctk.CTkFont(*TypeScale.body_large))
        kwargs.setdefault("height", 48)
        super().__init__(master, placeholder_text=placeholder, **kwargs)

    def focus_in(self, _event=None):
        s = ThemeManager.scheme
        self.configure(border_color=s.primary, border_width=2)

    def focus_out(self, _event=None):
        s = ThemeManager.scheme
        self.configure(border_color=s.outline, border_width=1)

    def bind_focus_effects(self):
        self.bind("<FocusIn>",  self.focus_in)
        self.bind("<FocusOut>", self.focus_out)
        return self


# ─────────────────────────────── ProgressBar ─────────────────────────────────

class M3LinearProgress(ctk.CTkProgressBar):
    """
    MD3 Linear Progress Indicator — thin, rounded, primary colour.
    """
    def __init__(self, master, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("corner_radius", Shape.full)
        kwargs.setdefault("height", 6)
        kwargs.setdefault("fg_color", s.surface_variant)
        kwargs.setdefault("progress_color", s.primary)
        super().__init__(master, **kwargs)
        self.set(0)


# ─────────────────────────────── Chip ────────────────────────────────────────

class M3FilterChip(ctk.CTkButton):
    """
    MD3 Filter / Suggestion Chip.
    Toggleable; changes background when selected.
    """
    def __init__(self, master, text: str = "", selected: bool = False, **kwargs):
        s = ThemeManager.scheme
        self._selected = selected
        kwargs.setdefault("corner_radius", Shape.small)
        kwargs.setdefault("height", 32)
        kwargs.setdefault("font", ctk.CTkFont(*TypeScale.label_large))
        kwargs.setdefault("border_width", 1)
        self._update_colors(kwargs)
        super().__init__(master, text=text, **kwargs)
        self.configure(command=self._toggle)

    def _update_colors(self, kw: dict | None = None) -> None:
        s = ThemeManager.scheme
        if self._selected:
            bg, fg, brd = s.secondary_cont, s.on_secondary_cont, s.secondary_cont
        else:
            bg, fg, brd = "transparent", s.on_surface_var, s.outline
        if kw is not None:
            kw.setdefault("fg_color",     bg)
            kw.setdefault("text_color",   fg)
            kw.setdefault("border_color", brd)
        else:
            self.configure(fg_color=bg, text_color=fg, border_color=brd)

    def _toggle(self) -> None:
        self._selected = not self._selected
        self._update_colors()

    @property
    def selected(self) -> bool:
        return self._selected


# ─────────────────────────────── NavRail ─────────────────────────────────────

class M3NavRail(ctk.CTkFrame):
    """
    Desktop Navigation Rail — vertical left sidebar equivalent of Android's
    BottomNavigationBar.

    Parameters
      ──────────
      items       : list of (label, icon_text), e.g. [("Home", "H"), ...]
      on_change   : callback(index: int)
    """

    def __init__(
        self,
        master,
        items     : list[tuple[str, str]],
        on_change : callable,
        on_library_click: callable | None = None,
        **kwargs,
    ):
        s = ThemeManager.scheme
        kwargs.setdefault("width", 188)
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("fg_color", s.surface_container)
        super().__init__(master, **kwargs)
        self.grid_propagate(False)
        self.pack_propagate(False)

        self._items     = items
        self._on_change = on_change
        self._on_library_click = on_library_click
        self._active    = 0
        self._btns: list[ctk.CTkButton] = []
        self._library_count_lbl: ctk.CTkLabel | None = None
        self._library_path_lbl: ctk.CTkLabel | None = None
        self._library_card: ctk.CTkFrame | None = None

        self._build()

    def _build(self) -> None:
        s = ThemeManager.scheme
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(24, 28))

        logo = ctk.CTkLabel(
            brand, text="P",
            font=ctk.CTkFont("", 30, "bold"),
            text_color=s.primary,
            width=36,
        )
        logo.pack(side="left")

        ctk.CTkLabel(
            brand,
            text="Ploxt",
            font=ctk.CTkFont(*TypeScale.title_large),
            text_color=s.on_surface,
            anchor="w",
        ).pack(side="left", padx=(10, 0))

        for i, (label, icon) in enumerate(self._items):
            btn = ctk.CTkButton(
                self,
                text=f"{icon}  {label}",
                font=ctk.CTkFont(*TypeScale.label_large),
                corner_radius=Shape.full,
                width=156 if i == 0 else 148, height=44,
                fg_color=s.primary_container if i == 0 else "transparent",
                hover_color=s.surface_variant,
                text_color=s.on_primary_cont if i == 0 else s.on_surface_var,
                anchor="w",
                command=lambda idx=i: self._on_btn_click(idx),
            )
            btn.pack(padx=20, pady=4)
            btn.bind("<Enter>", lambda _e, b=btn, idx=i: self._on_nav_hover(b, idx, True))
            btn.bind("<Leave>", lambda _e, b=btn, idx=i: self._on_nav_hover(b, idx, False))
            self._btns.append(btn)

        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        library = ctk.CTkFrame(
            self,
            fg_color=s.secondary_cont,
            corner_radius=Shape.large,
        )
        self._library_card = library
        library.pack(fill="x", padx=16, pady=(8, 18))

        ctk.CTkLabel(
            library,
            text="Library",
            font=ctk.CTkFont(*TypeScale.label_large),
            text_color=s.on_secondary_cont,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(12, 2))

        self._library_count_lbl = ctk.CTkLabel(
            library,
            text="Scanning...",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_secondary_cont,
            anchor="w",
        )
        self._library_count_lbl.pack(fill="x", padx=14, pady=(0, 2))

        self._library_path_lbl = ctk.CTkLabel(
            library,
            text="",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_secondary_cont,
            anchor="w",
            wraplength=132,
        )
        self._library_path_lbl.pack(fill="x", padx=14, pady=(0, 12))
        self._bind_library_card()

    def _select_ui_only(self, index: int) -> None:
        """Update selection styling without firing the page-change callback."""
        s = ThemeManager.scheme
        prev = self._btns[self._active]
        prev.configure(fg_color="transparent", text_color=s.on_surface_var)
        self._animate_width(prev, 148)
        self._active = index
        curr = self._btns[index]
        curr.configure(fg_color=s.primary_container, text_color=s.on_primary_cont)
        self._animate_width(curr, 156)

    def _on_btn_click(self, index: int) -> None:
        """Handle direct user clicks on a navigation button."""
        if index != self._active:
            self._select_ui_only(index)
            if self._on_change:
                self._on_change(index)

    def set_active(self, index: int) -> None:
        """Synchronize the selected navigation item from outside the rail."""
        if index != self._active:
            self._select_ui_only(index)

    def set_library_summary(self, count: int, folder: str) -> None:
        if self._library_count_lbl is None or self._library_path_lbl is None:
            return
        label = "No audio files" if count == 0 else f"{count} audio file{'s' if count != 1 else ''}"
        self._library_count_lbl.configure(text=label)
        self._library_path_lbl.configure(text=folder)

    def _animate_width(self, button: ctk.CTkButton, target: int, steps: int = 6) -> None:
        try:
            start = int(button.cget("width"))
        except Exception:
            start = target
        if start == target:
            return
        delta = (target - start) / steps

        def tick(step: int) -> None:
            width = round(start + delta * step)
            button.configure(width=width)
            if step < steps:
                self.after(18, lambda: tick(step + 1))

        tick(1)

    def _on_nav_hover(self, button: ctk.CTkButton, index: int, is_hovered: bool) -> None:
        if index == self._active:
            return
        s = ThemeManager.scheme
        button.configure(fg_color=s.surface_variant if is_hovered else "transparent")
        self._animate_width(button, 152 if is_hovered else 148, steps=4)

    def _bind_library_card(self) -> None:
        if self._library_card is None:
            return
        for widget in (self._library_card, *self._library_card.winfo_children()):
            try:
                widget.configure(cursor="hand2")
            except Exception:
                pass
            widget.bind("<Button-1>", lambda _e: self._on_library_click() if self._on_library_click else None)
            widget.bind("<Enter>", lambda _e: self._set_library_hover(True))
            widget.bind("<Leave>", lambda _e: self._set_library_hover(False))

    def _set_library_hover(self, is_hovered: bool) -> None:
        if self._library_card is None:
            return
        s = ThemeManager.scheme
        self._library_card.configure(fg_color=s.tertiary_cont if is_hovered else s.secondary_cont)


# ─────────────────────────────── Divider ─────────────────────────────────────

class M3Divider(ctk.CTkFrame):
    """1-px horizontal divider in outline-variant colour."""
    def __init__(self, master, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("height", 1)
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("fg_color", s.outline_variant)
        super().__init__(master, **kwargs)


# ─────────────────────────────── StatusBadge ─────────────────────────────────

class M3StatusBadge(ctk.CTkLabel):
    """Coloured pill badge for status display (downloading / done / error)."""

    STATUS_COLORS = {
        "downloading" : ("#1C4587", "#BEC2FF"),   # dark-bg, light-text
        "done"        : ("#1B5E20", "#A5D6A7"),
        "error"       : ("#7F0000", "#FFCDD2"),
        "pending"     : ("#3E2723", "#D7CCC8"),
    }

    def __init__(self, master, status: str = "pending", **kwargs):
        bg, fg = self.STATUS_COLORS.get(status, ("#333", "#EEE"))
        kwargs.setdefault("corner_radius", Shape.full)
        kwargs.setdefault("fg_color", bg)
        kwargs.setdefault("text_color", fg)
        kwargs.setdefault("font", ctk.CTkFont(*TypeScale.label_small))
        kwargs.setdefault("width", 90)
        kwargs.setdefault("height", 22)
        super().__init__(master, text=status.upper(), **kwargs)

    def set_status(self, status: str) -> None:
        bg, fg = self.STATUS_COLORS.get(status, ("#333", "#EEE"))
        self.configure(fg_color=bg, text_color=fg, text=status.upper())


# ─────────────────────────────── SectionLabel ────────────────────────────────

class M3SectionLabel(ctk.CTkLabel):
    """Title-small label used as a section header above groups of widgets."""
    def __init__(self, master, text: str = "", **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("font", ctk.CTkFont(*TypeScale.title_small))
        kwargs.setdefault("text_color", s.on_surface_var)
        super().__init__(master, text=text, **kwargs)


# ─────────────────────────────── DropdownMenu ────────────────────────────────

class M3DropdownMenu(ctk.CTkOptionMenu):
    """
    MD3-styled option menu (closest approximation to exposed dropdown).
    """
    def __init__(self, master, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("corner_radius", Shape.small)
        kwargs.setdefault("fg_color", s.surface_variant)
        kwargs.setdefault("button_color", s.surface_variant)
        kwargs.setdefault("button_hover_color", s.secondary_cont)
        kwargs.setdefault("dropdown_fg_color", s.surface_container)
        kwargs.setdefault("dropdown_hover_color", s.secondary_cont)
        kwargs.setdefault("text_color", s.on_surface)
        kwargs.setdefault("dropdown_text_color", s.on_surface)
        kwargs.setdefault("font", ctk.CTkFont(*TypeScale.body_medium))
        kwargs.setdefault("dropdown_font", ctk.CTkFont(*TypeScale.body_medium))
        kwargs.setdefault("height", 40)
        super().__init__(master, **kwargs)
