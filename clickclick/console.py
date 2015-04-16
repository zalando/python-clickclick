import click
import datetime
import time


def action(msg, **kwargs):
    click.secho(msg.format(**kwargs), nl=False, bold=True)


def ok(msg=' OK', **kwargs):
    click.secho(msg, fg='green', bold=True, **kwargs)


def error(msg, **kwargs):
    click.secho(' {}'.format(msg), fg='red', bold=True, **kwargs)


def warning(msg, **kwargs):
    click.secho(' {}'.format(msg), fg='yellow', bold=True, **kwargs)


def info(msg):
    click.secho('{}'.format(msg), fg='blue', bold=True)


class Action:

    def __init__(self, msg, **kwargs):
        self.msg = msg
        self.msg_args = kwargs
        self.errors = []

    def __enter__(self):
        action(self.msg, **self.msg_args)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if not self.errors:
                ok()
        else:
            error('EXCEPTION OCCURRED: {}'.format(exc_val))

    def error(self, msg, **kwargs):
        error(msg, **kwargs)
        self.errors.append(msg)

    def progress(self):
        click.secho(' .', nl=False)


def format_time(ts):
    if ts == 0:
        return ''
    now = datetime.datetime.now()
    try:
        dt = datetime.datetime.fromtimestamp(ts)
    except:
        return ts
    diff = now - dt
    s = diff.total_seconds()
    if s > 3600:
        t = '{:.0f}h'.format(s / 3600)
    elif s > 60:
        t = '{:.0f}m'.format(s / 60)
    else:
        t = '{:.0f}s'.format(s)
    return '{} ago'.format(t)


def format(col, val):
    if val is None:
        val = ''
    elif col.endswith('_time'):
        val = format_time(val)
    elif isinstance(val, bool):
        val = 'yes' if val else 'no'
    else:
        val = str(val)
    return val


def print_table(cols, rows, styles=None, titles=None, max_column_widths=None):
    if not styles:
        styles = {}

    if not titles:
        titles = {}

    if not max_column_widths:
        max_column_widths = {}

    colwidths = {}

    for col in cols:
        colwidths[col] = len(titles.get(col, col))

    for row in rows:
        for col in cols:
            val = row.get(col)
            colwidths[col] = min(max(colwidths[col], len(format(col, val))), max_column_widths.get(col, 1000))

    for i, col in enumerate(cols):
        click.secho(('{:' + str(colwidths[col]) + '}').format(titles.get(col, col.title().replace('_', ' '))),
                    nl=False, fg='black', bg='white')
        if i < len(cols)-1:
            click.secho('│', nl=False, fg='black', bg='white')
    click.echo('')

    for row in rows:
        for col in cols:
            val = row.get(col)
            align = ''
            try:
                style = styles.get(val, {})
            except:
                # val might not be hashable
                style = {}
            if val is not None and col.endswith('_time'):
                align = '>'
                diff = time.time() - val
                if diff < 900:
                    style = {'fg': 'green', 'bold': True}
                elif diff < 3600:
                    style = {'fg': 'green'}
            elif isinstance(val, int) or isinstance(val, float):
                align = '>'
            val = format(col, val)

            if len(val) > max_column_widths.get(col, 1000):
                val = val[:max_column_widths.get(col, 1000) - 2] + '..'
            click.secho(('{:' + align + str(colwidths[col]) + '}').format(val), nl=False, **style)
            click.echo(' ', nl=False)
        click.echo('')


def choice(prompt: str, options: list):
    """
    Ask to user to select one option and return it
    """
    click.secho(prompt)
    for i, option in enumerate(options):
        if isinstance(option, tuple):
            value, label = option
        else:
            value = label = option
        click.secho('{}) {}'.format(i+1, label))
    while True:
        selection = click.prompt('Please select (1-{})'.format(len(options)), type=int)
        try:
            result = options[int(selection)-1]
            if isinstance(result, tuple):
                value, label = result
            else:
                value = result
            return value
        except:
            pass


class AliasedGroup(click.Group):
    """
    Click group which allows using abbreviated commands
    """
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


class FloatRange(click.types.FloatParamType):
    """A parameter that works similar to :data:`click.FLOAT` but restricts
    the value to fit into a range.  The default behavior is to fail if the
    value falls outside the range, but it can also be silently clamped
    between the two edges.
    """
    name = 'float range'

    def __init__(self, min=None, max=None, clamp=False):
        self.min = min
        self.max = max
        self.clamp = clamp

    def convert(self, value, param, ctx):
        rv = click.types.FloatParamType.convert(self, value, param, ctx)
        if self.clamp:
            if self.min is not None and rv < self.min:
                return self.min
            if self.max is not None and rv > self.max:
                return self.max
        if self.min is not None and rv < self.min or \
           self.max is not None and rv > self.max:
            if self.min is None:
                self.fail('%s is bigger than the maximum valid value '
                          '%s.' % (rv, self.max), param, ctx)
            elif self.max is None:
                self.fail('%s is smaller than the minimum valid value '
                          '%s.' % (rv, self.min), param, ctx)
            else:
                self.fail('%s is not in the valid range of %s to %s.'
                          % (rv, self.min, self.max), param, ctx)
        return rv

    def __repr__(self):
        return 'FloatRange(%r, %r)' % (self.min, self.max)
