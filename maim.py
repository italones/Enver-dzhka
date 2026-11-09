using System;
using System.Numerics;
using System.Threading;

namespace PrimeFibApp
{
    public enum WorkerKind { Primes, Fibonacci }

    public class NumberWorker
    {
        private readonly WorkerKind _kind;
        private readonly long? _from;
        private readonly long? _to;
        private readonly Action<BigInteger> _onNumber;  // Invoke в UI делает вызывающий
        private readonly Action _onFinished;
        private readonly int _delayMs;

        private Thread _thread;
        private volatile bool _stop;
        private readonly ManualResetEventSlim _pauseEvent = new(true);

        public NumberWorker(WorkerKind kind, long? from, long? to,
                            Action<BigInteger> onNumber, Action onFinished,
                            int delayMs = 20)
        {
            _kind = kind;
            _from = from;
            _to = to;
            _onNumber = onNumber;
            _onFinished = onFinished;
            _delayMs = delayMs;
        }

        public void Start()
        {
            _stop = false;
            _pauseEvent.Set();
            _thread = new Thread(Run) { IsBackground = true, Name = _kind.ToString() };
            _thread.Start();
        }

        public void Pause()  => _pauseEvent.Reset();
        public void Resume() => _pauseEvent.Set();

        public void Stop()
        {
            _stop = true;
            _pauseEvent.Set();        // разбудить, если на паузе
            _thread?.Join(2000);      // дождаться завершения
        }

        private void Run()
        {
            try
            {
                if (_kind == WorkerKind.Primes) RunPrimes();
                else RunFibonacci();
            }
            catch (ThreadAbortException) { /* .NET Framework */ }
            catch (ThreadInterruptedException) { /* ignore */ }
            finally
            {
                _onFinished?.Invoke();
            }
        }

        private void RunPrimes()
        {
            long start = _from ?? 2;                  // по умолчанию старт с 2
            long end = _to ?? long.MaxValue;          // нет верхней — до бесконечности

            for (long n = start; n <= end && !_stop; n++)
            {
                _pauseEvent.Wait();
                if (_stop) return;

                if (IsPrime(n))
                {
                    _onNumber(n);
                    Thread.Sleep(_delayMs);
                }
            }
        }

        private void RunFibonacci()
        {
            BigInteger a = 0, b = 1;
            BigInteger? upper = _to.HasValue ? new BigInteger(_to.Value) : null;
            // нижняя граница для Фибоначчи не применяется (последовательность
            // начинается с 0/1); from игнорируется — это допущение задания.

            while (!_stop)
            {
                _pauseEvent.Wait();
                if (_stop) return;

                if (upper.HasValue && a > upper.Value) return;

                _onNumber(a);
                (a, b) = (b, a + b);
                Thread.Sleep(_delayMs);
            }
        }

        private static bool IsPrime(long n)
        {
            if (n < 2) return false;
            if (n % 2 == 0) return n == 2;
            for (long d = 3; d * d <= n; d += 2)
                if (n % d == 0) return false;
            return true;
        }
    }
}