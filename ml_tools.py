from typing import List

import numpy as np


def split_by_token(tokens: List[str], token):
  res = []
  sentence = []
  for i in tokens:
    if i == token:
      res.append(sentence)
      sentence = []
    else:
      sentence.append(i)

  res.append(sentence)
  return res


def estimate_threshold(a, min_th=0.3):
  return max(min_th, np.max(a) * 0.7)


def normalize(x, out_range=(0, 1)):
  domain = np.min(x), np.max(x)
  if (domain[1] - domain[0]) == 0:
    # all same
    return np.full(len(x), out_range[0])
    # raise ValueError('all elements are same')

  y = (x - (domain[1] + domain[0]) / 2) / (domain[1] - domain[0])
  return y * (out_range[1] - out_range[0]) + (out_range[1] + out_range[0]) / 2


def smooth_safe(x, window_len=10, window='hanning'):
  _blur = int(min(window_len, 2 + len(x) / 3.0))
  _blur = int(_blur / 2) * 2
  if (_blur > (len(x))):
    return x
  return smooth(x, window_len=_blur, window=window)


def smooth(x, window_len=11, window='hanning'):
  """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

  if x.ndim != 1:
    raise ValueError("smooth only accepts 1 dimension arrays.")

  if x.size < window_len:
    raise ValueError("Input vector needs to be bigger than window size.")

  if window_len < 3:
    return x

  if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
    raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

  s = np.r_[x[window_len - 1:0:-1], x, x[-2:-window_len - 1:-1]]
  # print(len(s))
  if window == 'flat':  # moving average
    w = np.ones(window_len, 'd')
  else:
    w = eval('np.' + window + '(window_len)')

  y = np.convolve(w / w.sum(), s, mode='valid')
  #     return y
  halflen = int(window_len / 2)
  #     return y[0:len(x)]
  return y[(halflen - 1):-halflen]


def relu(x, relu_th=0):
  assert type(x) is np.ndarray

  relu = x * (x > relu_th)
  return relu


def extremums(x):
  extremums = []
  extremums.append(0)
  for i in range(1, len(x) - 1):
    if x[i - 1] < x[i] > x[i + 1]:
      extremums.append(i)
  return extremums


def softmax(v):
  x = normalize(v)
  x /= len(x)
  return x


def make_echo(av, k=0.5):
  innertia = np.zeros(len(av))
  sum = 0

  for i in range(len(av)):
    if av[i] > k:
      sum = av[i]
    innertia[i] = sum
  #     sum-=0.0005
  return innertia


# def momentum(av, decay=0.9):
#   innertia = np.zeros(len(av))
#   m = 0
#   for i in range(len(innertia)):
#     m += av[i]
#     if m > 2:
#       m=2
#     innertia[i] = m

#     m *= decay

#   return innertia


# def momentum(av, decay=0.9):
#   m = np.zeros(len(av))
#   m[0]=av[0]
#   for i in range(len(av)):
#     m[i] = max(av[i], m[i-1]*decay)
#   return m

def momentum_(x, decay=0.99):
  innertia = np.zeros(len(x))
  m = 0
  for i in range(len(x)):
    m += x[i]
    innertia[i] = m
    m *= decay

  return innertia


def momentum(x, decay=0.999):
  innertia = np.zeros(len(x))
  m = 0
  for i in range(len(x)):
    m = max(m, x[i])
    innertia[i] = m
    m *= decay

  return innertia


def onehot_column(a, mask=-2 ** 32, replacement=None):
  """

  Searches for maximum in every column.
  Other elements are replaced with mask

  :param a:
  :param mask:
  :return:
  """
  maximals = np.max(a, 0)

  for i in range(a.shape[0]):
    for j in range(a.shape[1]):
      if a[i, j] < maximals[j]:
        a[i, j] = mask
      else:
        if replacement is not None:
          a[i, j] = replacement

  return a


def most_popular_in(arr):
  if len(arr) == 0:
    return None

  counts = np.bincount(arr)
  return np.argmax(counts)


def remove_similar_indexes(indexes, min_section_size=20):
  if len(indexes) < 2:
    return indexes

  indexes_zipped = []
  indexes_zipped.append(indexes[0])

  for i in range(1, len(indexes)):
    if indexes[i] - indexes[i - 1] > min_section_size:
      indexes_zipped.append(indexes[i])
  return indexes_zipped


def cut_above(x, threshold):
  return threshold + relu(x * -1 + threshold) * -1


def max_exclusive_pattern_by_prefix(distances_per_pattern_dict, prefix):
  _sum = None

  for p in distances_per_pattern_dict:
    if p.startswith(prefix):
      x = distances_per_pattern_dict[p]

      if _sum is None:
        _sum = np.zeros(len(x))

      _sum = np.maximum(_sum, x)

  return _sum
