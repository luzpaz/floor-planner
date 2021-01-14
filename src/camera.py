import sdl2

class Camera:
    """Dictates the user's view of the drawing.
    """

    # Regular camera scrolling speed (in/s)
    REGULAR_SCROLL_SPEED = 500

    # Fast camera scrolling (in/s)
    FAST_SCROLL_SPEED = 3000

    def __init__(self):
        """Initializes the camera class."""
        self.x = 0.0
        self.y = 0.0
        self.scale = 1.0

        self.last_scrolled = 0

    def scroll(self, keystate):
        """Scrolls the camera up, down, left, or right at normal or fast speed
        depending on the user's keyboard input.
        :param keystate: SDL keystate for checking currently pressed keys
        :type keystate: int[]
        """
        time_elapsed = (sdl2.SDL_GetTicks() - self.last_scrolled) / 1000.0
        self.last_scrolled = sdl2.SDL_GetTicks()

        if keystate[sdl2.SDL_SCANCODE_W] or keystate[sdl2.SDL_SCANCODE_UP]:
            if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                self.y -= Camera.FAST_SCROLL_SPEED * time_elapsed
            else:
                self.y -= Camera.REGULAR_SCROLL_SPEED * time_elapsed

        if keystate[sdl2.SDL_SCANCODE_S] or keystate[sdl2.SDL_SCANCODE_DOWN]:
            if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                self.y += Camera.FAST_SCROLL_SPEED * time_elapsed
            else:
                self.y += Camera.REGULAR_SCROLL_SPEED * time_elapsed

        if keystate[sdl2.SDL_SCANCODE_A] or keystate[sdl2.SDL_SCANCODE_LEFT]:
            if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                self.x -= Camera.FAST_SCROLL_SPEED * time_elapsed
            else:
                self.x -= Camera.REGULAR_SCROLL_SPEED * time_elapsed

        if keystate[sdl2.SDL_SCANCODE_D] or keystate[sdl2.SDL_SCANCODE_RIGHT]:
            if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                self.x += Camera.FAST_SCROLL_SPEED * time_elapsed
            else:
                self.x += Camera.REGULAR_SCROLL_SPEED * time_elapsed
